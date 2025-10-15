import UfilterLogo from "@/assets/Ufilter.svg";

export const NavBar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-content">
        <img src={UfilterLogo} alt="U-Filter Logo" className="navbar-logo" />
      </div>
    </nav>
  );
};
